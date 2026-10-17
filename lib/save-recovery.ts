import { GAME_SAVE_KEY } from './save-data';

export const SAVE_BACKUP_PREFIX = `${GAME_SAVE_KEY}:backup:`;

export class SaveRecoveryChangedError extends Error {
  constructor() {
    super('The saved game changed. Reopen it before starting fresh.');
    this.name = 'SaveRecoveryChangedError';
  }
}

type RecoveryStorage = {
  getItem: (key: string) => Promise<string | null>;
  setItem: (key: string, value: string) => Promise<void>;
};

/**
 * Keep the rejected bytes before replacing the primary save. The caller supplies
 * a fresh unique backup ID; backup values are never read, overwritten or deleted.
 * AsyncStorage has no atomic compare-and-swap, so these checks cannot exclude an
 * external writer changing the primary save between the last read and write.
 */
export async function backupBeforeFreshStart(
  storage: RecoveryStorage,
  options: {
    expectedRaw: string;
    backupId: string;
    freshRaw: string;
    isCurrent: () => boolean;
  },
): Promise<void> {
  const { expectedRaw, backupId, freshRaw, isCurrent } = options;
  if (!backupId.trim()) throw new Error('A unique save backup ID is required.');

  async function assertCurrent() {
    if (!isCurrent()) throw new SaveRecoveryChangedError();
    const raw = await storage.getItem(GAME_SAVE_KEY);
    if (!isCurrent() || raw !== expectedRaw) throw new SaveRecoveryChangedError();
  }

  await assertCurrent();
  await storage.setItem(`${SAVE_BACKUP_PREFIX}${backupId}`, expectedRaw);
  await assertCurrent();
  await storage.setItem(GAME_SAVE_KEY, freshRaw);
}
