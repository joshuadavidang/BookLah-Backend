import { authService } from "@/services/authService";
import { Context } from "koa";
import dotenv from "dotenv";
dotenv.config();

const AuthService = new authService();
const REDIRECT_URL = String(process.env.REDIRECT_URL);

async function getAuthUrl(ctx: Context) {
  const url = await AuthService.getAuthUrl(ctx);
  ctx.body = { url };
}

async function authenticateUser(ctx: Context) {
  const result = await AuthService.authenticateUser(ctx);
  if (!result) {
    ctx.body = { code: 401, msg: "User not authenticated." };
    return;
  }
  ctx.redirect(REDIRECT_URL);
}

async function getUserData(ctx: Context) {
  const userData = await AuthService.getUserInfo(ctx);
  if (!userData) {
    ctx.body = { code: 401, msg: "Unauthorised Request" };
    return;
  }
  ctx.body = { code: 200, msg: "Successfully fetched user data", userData };
}

export { getAuthUrl, authenticateUser, getUserData };
