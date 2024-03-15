import { AppDataSource } from "@/config/db";
import { ErrorsType } from "@/helpers/errors";
import User from "@/models/Users";
import { UserType } from "@/types";

class userService {
  public async isUserExist(userId: string) {
    const dataRepository = AppDataSource.getRepository(User);
    const result = await dataRepository.findOne({
      where: {
        userId: userId,
      },
    });
    return result;
  }

  public async saveUserInformation(
    userId: string,
    name: string,
    gender: string,
    userType: UserType
  ) {
    const result = await this.isUserExist(userId);
    if (result === null) {
      const newUser = new User();
      newUser.userId = userId;
      newUser.name = name;
      newUser.gender = gender;
      newUser.userType = userType;
      return AppDataSource.manager.save(newUser);
    } else {
      console.log(ErrorsType.USER_EXIST);
    }
  }

  public fetchUserData() {
    return;
  }
}

export { userService };
