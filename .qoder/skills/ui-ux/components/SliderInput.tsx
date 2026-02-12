import { InputNumber, Slider } from 'antd';

const DecimalStep = ({
  disabled = false,
  max = 1,
  min = 0,
  onChange,
  step = 0.01,
  value,
}: Props) => {
  return (
    <div className="flex items-center">
      <Slider
        className="flex-1"
        disabled={disabled}
        max={max}
        min={min}
        onChange={onChange}
        step={step}
        value={value}
      />
      <InputNumber
        className="w-[100px]"
        disabled={disabled}
        max={max}
        min={min}
        onChange={onChange}
        step={step}
        style={{ margin: '0 16px' }}
        value={value}
      />
    </div>
  );
};

interface Props {
  disabled?: boolean;
  max?: number;
  min?: number;
  onChange?: (value: null | number) => void;
  step?: number;
  value?: number;
}

/**
 * SliderInput - 滑块与数字输入组合组件
 * 
 * 用于调整数值参数，提供滑块和数字输入框两种交互方式
 * 
 * @example
 * ```tsx
 * // 小数范围
 * <Form.Item label="相似度阈值" name="similarityThreshold">
 *   <SliderInput min={0} max={1} step={0.01} />
 * </Form.Item>
 * 
 * // 整数范围
 * <Form.Item label="召回数量" name="size">
 *   <SliderInput min={1} max={100} step={1} />
 * </Form.Item>
 * ```
 */
const SliderInput = (props: Props) => (
  <>
    <DecimalStep {...props} />
  </>
);

export default SliderInput;
