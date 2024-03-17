import { userService } from "@/services/userService";

const UserService = new userService();

async function saveUserInformation(ctx: any) {
  const { userId, name, userType } = ctx.request.body;
  const result = await UserService.saveUserInformation(userId, name, userType);
  ctx.body = { result };
}

export { saveUserInformation };
