import { AppDataSource } from "@/config/db";
import { ErrorsType } from "@/helpers/errors";
import User from "@/models/Users";

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
    gender: string
  ) {
    const result = await this.isUserExist(userId);
    if (result === null) {
      const newUser = new User();
      newUser.userId = userId;
      newUser.name = name;
      newUser.gender = gender;
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
