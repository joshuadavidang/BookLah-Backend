import { UserType } from "@/types";
import { Column, Entity, PrimaryGeneratedColumn } from "typeorm";

@Entity()
export default class Users {
  @PrimaryGeneratedColumn("uuid")
  id: string;

  @Column()
  userId: string;

  @Column()
  name: string;

  @Column({
    type: "enum",
    enum: UserType,
  })
  userType: UserType;
}
