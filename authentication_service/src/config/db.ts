import dotenv from "dotenv";
dotenv.config();

import { DatabaseType, DataSource } from "typeorm";
import Users from "@/models/Users";

const progresDatabase: DatabaseType = "postgres";

const AppDataSource = new DataSource({
  type: progresDatabase,
  host: process.env.HOST,
  port: Number(process.env.DB_PORT),
  username: process.env.USERNAME,
  password: process.env.PASSWORD,
  database: process.env.DATABASE,
  entities: [Users],
  synchronize: true,
});

async function initialiseDatabase() {
  try {
    await AppDataSource.initialize();
    console.log("Database Initialised! 🔥");
  } catch (err) {
    console.log(err);
  }
}

export { AppDataSource, initialiseDatabase };
