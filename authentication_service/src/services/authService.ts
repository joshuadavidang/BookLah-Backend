import { sgid } from "@/config/sgId";
import { UserInfoReturn, generatePkcePair } from "@opengovsg/sgid-client";
import crypto from "crypto";
import { Context } from "koa";

type SessionData = Record<
  string,
  | {
      nonce?: string;
      state?: URLSearchParams;
      accessToken?: string;
      codeVerifier?: string;
      sub?: string;
    }
  | undefined
>;

class authService {
  sessionData: SessionData = {};
  SESSION_COOKIE_NAME = "userAuthenticatedSession";
  SESSION_COOKIE_OPTIONS = {
    httpOnly: true,
    maxAge: 900000, // Expires in 15 minutes
  };

  public async authenticate(ctx: Context): Promise<string> {
    const sessionId = crypto.randomUUID();
    const { codeChallenge, codeVerifier } = generatePkcePair();
    const { url, nonce } = sgid.authorizationUrl({
      codeChallenge,
      scope: ["openid", "myinfo.name"],
    });
    this.sessionData[sessionId] = {
      nonce,
      codeVerifier,
    };
    ctx.cookies.set(
      this.SESSION_COOKIE_NAME,
      sessionId,
      this.SESSION_COOKIE_OPTIONS
    );
    return url;
  }

  public async setCredentials(ctx: Context): Promise<boolean> {
    const authCode = String(ctx.query.code);
    const sessionId = String(ctx.cookies.get(this.SESSION_COOKIE_NAME));
    const session = this.sessionData[sessionId];

    if (!session?.codeVerifier) {
      return false;
    }

    const { accessToken, sub } = await sgid.callback({
      code: authCode,
      nonce: session.nonce,
      codeVerifier: session.codeVerifier,
    });

    session.accessToken = accessToken;
    session.sub = sub;
    this.sessionData[sessionId] = session;
    return true;
  }

  public async getUserInfo(ctx: Context): Promise<UserInfoReturn | boolean> {
    const sessionId = String(ctx.cookies.get(this.SESSION_COOKIE_NAME));
    const session = this.sessionData[sessionId];
    const accessToken = session?.accessToken;
    const sub = session?.sub;

    if (
      session === undefined ||
      accessToken === undefined ||
      sub === undefined
    ) {
      return false;
    }

    const userInfo = await sgid.userinfo({
      accessToken,
      sub,
    });

    return userInfo;
  }
}

export { authService };
