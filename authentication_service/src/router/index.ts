import {
  authenticateUser,
  getUserData,
  redirectUser,
} from "@/controllers/authController";
import Router from "@koa/router";
import dotenv from "dotenv";
dotenv.config();

const router = new Router();
const API_VERSION = process.env.API_VERSION;

router.get(`${API_VERSION}/`, async (ctx: any) => {
  ctx.body = "Server is Running! 💨";
});

router.get(`${API_VERSION}/auth`, authenticateUser);
router.get(`${API_VERSION}/redirect`, redirectUser);
router.get(`${API_VERSION}/userData`, getUserData);

export default router;
