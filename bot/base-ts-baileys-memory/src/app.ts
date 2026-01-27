import { join } from 'path'
import { createBot, createProvider, createFlow, addKeyword, utils } from '@builderbot/bot'
import { MemoryDB as Database } from '@builderbot/bot'
import { BaileysProvider as Provider } from '@builderbot/provider-baileys'
import { monitorFalls, monitorDeviceChanges } from './services/firebase'

const PORT = process.env.PORT ?? 3008

const discordFlow = addKeyword<Provider, Database>('doc').addAnswer(
    ['You can see the documentation here', '📄 https://builderbot.app/docs \n', 'Do you want to continue? *yes*'].join(
        '\n'
    ),
    { capture: true },
    async (ctx, { gotoFlow, flowDynamic }) => {
        if (ctx.body.toLocaleLowerCase().includes('yes')) {
            return gotoFlow(registerFlow)
        }
        await flowDynamic('Thanks!')
        return
    }
)

const welcomeFlow = addKeyword<Provider, Database>(['hi', 'hello', 'hola'])
    .addAnswer(`🙌 Hello welcome to this *Chatbot*`)
    .addAnswer(
        [
            'I share with you the following links of interest about the project',
            '👉 *doc* to view the documentation',
        ].join('\n'),
        { delay: 800, capture: true },
        async (ctx, { fallBack }) => {
            if (!ctx.body.toLocaleLowerCase().includes('doc')) {
                return fallBack('You should type *doc*')
            }
            return
        },
        [discordFlow]
    )

const registerFlow = addKeyword<Provider, Database>(utils.setEvent('REGISTER_FLOW'))
    .addAnswer(`What is your name?`, { capture: true }, async (ctx, { state }) => {
        await state.update({ name: ctx.body })
    })
    .addAnswer('What is your age?', { capture: true }, async (ctx, { state }) => {
        await state.update({ age: ctx.body })
    })
    .addAction(async (_, { flowDynamic, state }) => {
        await flowDynamic(`${state.get('name')}, thanks for your information!: Your age: ${state.get('age')}`)
    })

const fullSamplesFlow = addKeyword<Provider, Database>(['samples', utils.setEvent('SAMPLES')])
    .addAnswer(`💪 I'll send you a lot files...`)
    .addAnswer(`Send image from Local`, { media: join(process.cwd(), 'assets', 'sample.png') })
    .addAnswer(`Send video from URL`, {
        media: 'https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExYTJ0ZGdjd2syeXAwMjQ4aWdkcW04OWlqcXI3Ynh1ODkwZ25zZWZ1dCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/LCohAb657pSdHv0Q5h/giphy.mp4',
    })
    .addAnswer(`Send audio from URL`, { media: 'https://cdn.freesound.org/previews/728/728142_11861866-lq.mp3' })
    .addAnswer(`Send file from URL`, {
        media: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
    })

const main = async () => {
    const adapterFlow = createFlow([welcomeFlow, registerFlow, fullSamplesFlow])

    const adapterProvider = createProvider(Provider,
        { version: [2, 3000, 1027934701] as any }
    )
    const adapterDB = new Database()

    const { handleCtx, httpServer } = await createBot({
        flow: adapterFlow,
        provider: adapterProvider,
        database: adapterDB,
    })

    adapterProvider.server.post(
        '/v1/messages',
        handleCtx(async (bot, req, res) => {
            const { number, message, urlMedia } = req.body
            await bot.sendMessage(number, message, { media: urlMedia ?? null })
            return res.end('sended')
        })
    )

    adapterProvider.server.post(
        '/v1/register',
        handleCtx(async (bot, req, res) => {
            const { number, name } = req.body
            await bot.dispatch('REGISTER_FLOW', { from: number, name })
            return res.end('trigger')
        })
    )

    adapterProvider.server.post(
        '/v1/samples',
        handleCtx(async (bot, req, res) => {
            const { number, name } = req.body
            await bot.dispatch('SAMPLES', { from: number, name })
            return res.end('trigger')
        })
    )

    adapterProvider.server.post(
        '/v1/blacklist',
        handleCtx(async (bot, req, res) => {
            const { number, intent } = req.body
            if (intent === 'remove') bot.blacklist.remove(number)
            if (intent === 'add') bot.blacklist.add(number)

            res.writeHead(200, { 'Content-Type': 'application/json' })
            return res.end(JSON.stringify({ status: 'ok', number, intent }))
        })
    )

    adapterProvider.server.get(
        '/v1/blacklist/list',
        handleCtx(async (bot, req, res) => {
            const blacklist = bot.blacklist.getList()
            res.writeHead(200, { 'Content-Type': 'application/json' })
            return res.end(JSON.stringify({ status: 'ok', blacklist }))
        })
    )


    // Start monitoring falls
    const EMERGENCY_CONTACT = '56912345678' // TODO: Replace with real emergency number
    monitorFalls(async (data) => {
        const { lat, lng, timestamp } = data;
        const date = timestamp?.toDate ? timestamp.toDate().toLocaleString() : new Date().toLocaleString();

        const mapLink = lat && lng ? `https://maps.google.com/?q=${lat},${lng}` : 'Ubicación desconocida';

        const message = [
            '🚨 *ALERTA DE CAÍDA DETECTADA* 🚨',
            `📅 Fecha: ${date}`,
            `📍 Ubicación: ${mapLink}`,
            '',
            'Por favor verifique el estado del usuario.'
        ].join('\n');

        console.log(`Sending fall alert to ${EMERGENCY_CONTACT}`);
        await adapterProvider.sendMessage(EMERGENCY_CONTACT, message, {});
    });

    // Start monitoring device changes
    const DEVICE_ID = '3707806493';
    const ADMIN_NUMBER = '56996575503';

    monitorDeviceChanges(DEVICE_ID, async (data) => {
        const formatValue = (val: any) => {
            if (val && val.toDate) return val.toDate().toLocaleString(); // Handle Firestore Timestamps
            if (val === undefined || val === null) return 'N/A';
            return val;
        };

        const message = [
            `📡 *Device Update: ${DEVICE_ID}*`,
            `⚙️ Fall Configured: ${formatValue(data.fall_detection_configured)}`,
            `🕒 Configured At: ${formatValue(data.fall_detection_configured_at)}`,
            `🔋 Battery: ${formatValue(data.last_battery)}%`,
            `❤️ BP: ${formatValue(data.last_bp)} (Sys: ${formatValue(data.last_bp_sys)} / Dia: ${formatValue(data.last_bp_dia)})`,
            `📩 Last Cmd: ${formatValue(data.last_command_raw)}`,
            `↩️ Cmd Reply: ${formatValue(data.last_command_reply)}`,
            `⏲️ Cmd Time: ${formatValue(data.last_command_timestamp)}`,
            `📍 GPS Time: ${formatValue(data.last_gps_timestamp)}`,
            `🏥 Health Time: ${formatValue(data.last_health_timestamp)}`,
            `💓 HR: ${formatValue(data.last_hr)}`,
            `🌎 Location: ${formatValue(data.last_lat)}, ${formatValue(data.last_lng)}`,
            `👀 Last Seen: ${formatValue(data.last_seen)}`,
            `💨 SpO2: ${formatValue(data.last_spo2)}`,
            `🟢 Online: ${formatValue(data.online)}`,
            `👣 Steps: ${formatValue(data.steps_today)}`,
            `🔄 Updated At: ${formatValue(data.updated_at)}`
        ].join('\n');

        console.log(`Sending device update to ${ADMIN_NUMBER}`);
        await adapterProvider.sendMessage(ADMIN_NUMBER, message, {});
    });

    httpServer(+PORT)
}

main()
