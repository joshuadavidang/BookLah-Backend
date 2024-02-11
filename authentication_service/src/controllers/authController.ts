import { authService } from "@/services/authService";
import { Context } from "koa";
import dotenv from "dotenv";
dotenv.config();

const AuthService = new authService();

async function authenticateUser(ctx: Context) {
  const url = await AuthService.authenticate(ctx);
  ctx.body = { url };
}

async function redirectUser(ctx: Context) {
  const result = await AuthService.setCredentials(ctx);
  if (!result) {
    ctx.body = { code: 401, msg: "User not authenticated." };
    return;
  }
  const REDIRECT_URL = String(process.env.REDIRECT_URL);
  ctx.redirect(REDIRECT_URL);
}

async function getUserData(ctx: Context) {
  const userData = await AuthService.getUserInfo(ctx);
  if (!userData) {
    ctx.body = { code: 440, msg: "User session expired" };
    return;
  }
  ctx.body = { code: 200, msg: "Successfully fetched user data", userData };
}

export { authenticateUser, redirectUser, getUserData };
