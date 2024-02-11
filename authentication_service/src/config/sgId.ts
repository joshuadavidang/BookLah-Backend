import { SgidClient } from "@opengovsg/sgid-client";
import dotenv from "dotenv";
dotenv.config();

const PORT = process.env.SERVER_PORT;
const API_VERSION = process.env.API_VERSION;

const sgid = new SgidClient({
  clientId: String(process.env.SGID_CLIENT_ID),
  clientSecret: String(process.env.SGID_CLIENT_SECRET),
  privateKey: String(process.env.SGID_PRIVATE_KEY),
  redirectUri: `http://localhost:${PORT}${API_VERSION}/redirect`,
});

export { sgid };
