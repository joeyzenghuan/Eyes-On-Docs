export function validateAdminPassword(password: string | null | undefined) {
  const correctPassword = process.env.ADMIN_PASSWORD;

  if (!correctPassword) {
    return {
      ok: false,
      status: 500,
      error: '系统配置错误：未设置管理员密码'
    };
  }

  if (password !== correctPassword) {
    return {
      ok: false,
      status: 401,
      error: '密码错误'
    };
  }

  return {
    ok: true,
    status: 200,
    error: null
  };
}
