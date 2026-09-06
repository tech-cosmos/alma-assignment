import { NextResponse, type NextRequest } from "next/server";

/**
 * Guard the internal area. The API sets an httpOnly cookie on login; we only check for its
 * presence here (the API validates the JWT on every request and the /leads page bounces to
 * /login on a 401). Cookie name is configurable to match the backend.
 */
const AUTH_COOKIE = process.env.AUTH_COOKIE_NAME || "access_token";

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const authenticated = Boolean(request.cookies.get(AUTH_COOKIE)?.value);

  if (pathname.startsWith("/leads") && !authenticated) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = "";
    url.searchParams.set("next", `${pathname}${search}`);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/leads/:path*"],
};
