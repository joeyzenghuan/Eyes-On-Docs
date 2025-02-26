interface Window {
  gtag: (
    command: 'set',
    targetId: string,
    config: { [key: string]: any } | string
  ) => void;
}

declare function gtag(
  command: 'set',
  targetId: string,
  config: { [key: string]: any } | string
): void;