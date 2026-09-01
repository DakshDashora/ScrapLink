import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./slices/authSlices";

const loggerMiddleware = (store) => (next) => (action) => {
  console.log("Dispatching:", action);
  console.log("State before:", store.getState());

  const result = next(action);

  console.log("State after:", store.getState());
  return result;
};

export const store = configureStore({
  reducer: {
    auth: authReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(loggerMiddleware),
  devTools: true,
});

export default store;