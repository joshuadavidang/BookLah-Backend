import cors from "@koa/cors";
import dotenv from "dotenv";
import Koa from "koa";
import parser from "koa-bodyparser";
import router from "@/router";
import "reflect-metadata";

dotenv.config();

const app = new Koa();

app.use(
  cors({
    credentials: true,
  })
);
app.use(parser());
app.use(router.routes());

export { app };
