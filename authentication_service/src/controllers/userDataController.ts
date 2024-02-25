import { userService } from "@/services/UserService";

const UserService = new userService();

async function saveUserInformation(ctx: any) {
  const { userId, name, gender } = ctx.request.body;
  const result = await UserService.saveUserInformation(userId, name, gender);
  ctx.body = { result };
}

export { saveUserInformation };
