import React, { useState } from "react";
import { useSelector } from "react-redux";

import Login from "./components/auth/Login";
import Register from "./components/auth/Register";
import Verification from "./components/auth/Verification";

function AppContent() {
  const [isLogin, setIsLogin] = useState(true);
  const [showVerification, setShowVerification] = useState(false);

  const user = useSelector((state) => state.auth.user);

  const handleRegistrationSuccess = () => setShowVerification(true);
  const handleVerificationComplete = () => {
    setShowVerification(false);
    setIsLogin(true);
  };

  if (showVerification) {
    return <Verification onComplete={handleVerificationComplete} />;
  }

  return isLogin ? (
    <Login onSwitchToRegister={() => setIsLogin(false)} />
  ) : (
    <Register
      onSwitchToLogin={() => setIsLogin(true)}
      onRegistrationSuccess={handleRegistrationSuccess}
    />
  );
}

export default function App() {
  return <AppContent />;
}