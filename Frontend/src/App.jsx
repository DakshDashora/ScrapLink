import React, { useState } from "react";
import { Provider } from "react-redux";
import store from "./redux/store";

import Login from "./components/auth/Login";
import Register from "./components/auth/Register";

function App() {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <Provider store={store}>
      {isLogin ? (
        <Login onSwitchToRegister={() => setIsLogin(false)} />
      ) : (
        <Register onSwitchToLogin={() => setIsLogin(true)} />
      )}
    </Provider>
  );
}

export default App;