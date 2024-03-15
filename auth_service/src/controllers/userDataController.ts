import { userService } from "@/services/userService";

const UserService = new userService();

async function saveUserInformation(ctx: any) {
  const { userId, name, gender, userType } = ctx.request.body;
  const result = await UserService.saveUserInformation(
    userId,
    name,
    gender,
    userType
  );
  ctx.body = { result };
}

export { saveUserInformation };
