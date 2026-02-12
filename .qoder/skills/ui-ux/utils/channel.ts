/**
 * Channel - 跨Tab通信工具
 * 基于 BroadcastChannel API 实现跨浏览器标签页通信
 * 
 * @usage
 * ```typescript
 * const channel = Channel.getInstance();
 * 
 * // 添加监听事件
 * channel.addAction('workspace-change', () => {
 *   // 其他Tab切换了工作空间，刷新页面
 *   window.location.reload();
 * });
 * 
 * // 发送消息到其他Tab
 * channel.postMessage('workspace-change');
 * 
 * // 移除监听
 * channel.removeAction('workspace-change');
 * ```
 */
export class Channel {
  private static actionMap: Map<string, () => void>;
  private static instance: Channel | undefined;
  private channel: BroadcastChannel | undefined;

  private constructor() {
    Channel.actionMap = new Map<string, () => void>();
    try {
      this.channel = new BroadcastChannel('ai-dev');
      this.channel.addEventListener('message', (event: MessageEvent) => {
        const key = event.data as string;
        if (Channel.actionMap.has(key)) {
          const action = Channel.actionMap.get(key);
          if (action) {
            action();
          }
        }
      });

      // 添加错误处理
      this.channel.addEventListener('error', (event: Event) => {
        console.error('Channel error:', event);
      });
    } catch (error) {
      console.error('Failed to create BroadcastChannel:', error);
    }
  }

  public static getInstance(): Channel {
    Channel.instance ??= new Channel();
    return Channel.instance;
  }

  public addAction(key: string, action: () => void) {
    if (Channel.actionMap.has(key)) {
      console.warn(`Action for key "${key}" already exists. Overwriting.`);
    }
    Channel.actionMap.set(key, action);
  }

  public postMessage(key: string) {
    if (Channel.actionMap.has(key)) {
      const action = Channel.actionMap.get(key);
      if (action && Channel.instance?.channel) {
        Channel.instance.channel.postMessage(key);
      }
    }
  }

  public removeAction(key: string) {
    if (Channel.actionMap.has(key)) {
      Channel.actionMap.delete(key);
    } else {
      console.warn(`No action found for key "${key}".`);
    }
  }
}
