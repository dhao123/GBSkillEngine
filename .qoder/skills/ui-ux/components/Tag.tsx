/**
 * Tag - 自定义标签组件
 * 
 * 用于知识库标签、分类标记等场景
 * 
 * @example
 * ```tsx
 * <Tag name="机器学习" id={1} />
 * <Tag name="深度学习" className="custom-class" />
 * ```
 */
export default function Tag({
  className,
  id,
  name,
}: {
  className?: string;
  id?: number;
  name: string;
}) {
  return (
    <span
      className={`inline-block bg-[#E8EFFF] h-[20px] text-[#5293FE] text-[12px] rounded-[5px] leading-[20px] px-[10px] mr-[10px] ${className ?? ''}`}
      key={id}>
      {name}
    </span>
  );
}
