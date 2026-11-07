export class UnsupportedStatementError extends Error {
  override name = 'UnsupportedStatementError'
}

export class StatementParseError extends Error {
  override name = 'StatementParseError'
}

export class PasswordRequiredError extends Error {
  override name = 'PasswordRequiredError'
}

export class IncorrectPasswordError extends Error {
  override name = 'IncorrectPasswordError'
}
