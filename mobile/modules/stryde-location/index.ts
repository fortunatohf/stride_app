import { requireOptionalNativeModule, type EventSubscription } from 'expo-modules-core';

export type NativePoint = {
  t: number; // epoch milliseconds
  lat: number;
  lon: number;
  alt: number | null;
  acc: number | null; // horizontal accuracy, meters
  speed: number | null; // m/s as reported by the OS
};

export type StartOptions = {
  /** Android: desired interval between fixes. iOS delivers fixes as fast as the GPS allows (~1 Hz). */
  intervalMs?: number;
  /** Android foreground-service notification text (required by Android while recording). */
  notificationTitle?: string;
  notificationBody?: string;
};

type Events = { onLocation: (p: NativePoint) => void; onError: (e: { message: string }) => void };

interface StrydeLocationNative {
  start(options: StartOptions): Promise<void>;
  stop(): Promise<void>;
  isRecording(): boolean;
  /** Points buffered natively (also written to disk) since `fromIndex`. Survives JS reloads. */
  getBufferedPoints(fromIndex: number): Promise<NativePoint[]>;
  clearBuffer(): Promise<void>;
  addListener<K extends keyof Events>(event: K, listener: Events[K]): EventSubscription;
}

/** Null when running in Expo Go or a build without the native module; the recorder then falls back to expo-location. */
export const StrydeLocation = requireOptionalNativeModule<StrydeLocationNative>('StrydeLocation');
