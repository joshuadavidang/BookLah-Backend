import { app } from "./index";
import cors from "@koa/cors";

const PORT = process.env.SERVER_PORT || 3001;

app.use(
  cors({
    credentials: true,
  })
);
app.listen(PORT, () => {
  console.log(`🚀 Server listening on localhost:${PORT} 🚀`);
});
