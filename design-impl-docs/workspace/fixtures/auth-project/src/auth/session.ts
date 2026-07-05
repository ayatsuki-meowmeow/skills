export const SESSION_TTL_MINUTES = 60;

export type Session = {
  id: string;
  userId: string;
  createdAt: Date;
  expiresAt: Date;
};

export function createSession(userId: string): Session {
  const now = new Date();
  return {
    id: crypto.randomUUID(),
    userId,
    createdAt: now,
    expiresAt: new Date(now.getTime() + SESSION_TTL_MINUTES * 60 * 1000),
  };
}

export function isSessionValid(session: Session, now: Date = new Date()): boolean {
  return session.expiresAt.getTime() > now.getTime();
}
