import {
  getAuthUrl,
  getUserData,
  authenticateUser,
} from "@/controllers/authController";
import Router from "@koa/router";
import dotenv from "dotenv";
dotenv.config();

const router = new Router();
const API_VERSION = String(process.env.API_VERSION);
router.prefix(API_VERSION);

router.get(`${API_VERSION}/`, async (ctx: any) => {
  ctx.body = "Server is Running! 💨";
});

router.get("/getAuthUrl", getAuthUrl);
router.get("/authenticateUser", authenticateUser);
router.get("/userData", getUserData);

export default router;
