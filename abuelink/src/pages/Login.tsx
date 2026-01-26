import React from "react";
import { signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "../services/firebase";
import { useNavigate } from "react-router-dom";

const Login: React.FC = () => {
  const navigate = useNavigate();

  const handleGoogleSignIn = async () => {
    try {
      await signInWithPopup(auth, googleProvider);
      navigate("/");
    } catch (error) {
      console.error("Error signing in with Google:", error);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100vh" }}>
      <h1>Abuelink</h1>
      <p>Conecta con tus seres queridos</p>
      <button
        onClick={handleGoogleSignIn}
        style={{ padding: "10px 20px", fontSize: "16px", cursor: "pointer", borderRadius: "5px", border: "1px solid #ccc", background: "white" }}
      >
        Iniciar sesión con Google
      </button>
    </div>
  );
};

export default Login;
