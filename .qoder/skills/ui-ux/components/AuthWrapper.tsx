/**
 * AuthWrapper - 权限包装器组件
 * 统一处理按钮和功能的权限控制
 * 
 * @usage
 * ```tsx
 * <AuthWrapper code="AIDEV-APP-RECOMMEND">
 *   <Button>推荐应用</Button>
 * </AuthWrapper>
 * ```
 */
import { use } from 'react';

import type { AuthCode } from '../constants';

import { CommonContext, type ContextType } from '../core/context';

export default function AuthWrapper({
  children,
  code,
}: {
  children: React.ReactNode;
  code: AuthCode;
}) {
  const contextValue = use<ContextType>(CommonContext);
  return contextValue.authList.includes(code) ? children : null;
}
