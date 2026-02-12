import type { BannerType } from './BannerConstants';
import { PageHeaderBannerConfig } from './BannerConstants';
import helperBg from '../assets/banner/helper.png';

/**
 * Banner - 页面横幅组件
 * 
 * 用于功能模块入口页的顶部横幅展示，包含主横幅和教程入口
 * 
 * @example
 * ```tsx
 * import Banner from '@/components/Banner';
 * 
 * const ModelPage = () => {
 *   return (
 *     <div>
 *       <Banner type="model" />
 *       {/* 页面内容 *\/}
 *     </div>
 *   );
 * };
 * ```
 */
const Banner = (props: { type: BannerType }) => {
  const { type } = props;
  const {
    bannerBg,
    description,
    helperLink,
    helperText,
    needsHelper,
    openNewTab = false,
    title,
  } = PageHeaderBannerConfig[type];

  return (
    <div className="flex w-full h-[120px] justify-between">
      {/* 主横幅 */}
      <div className={`w-[74%] h-[120px] relative ${needsHelper ? '' : 'w-full'}`}>
        <img
          alt=""
          className="w-full h-full object-cover rounded-[8px] contrast-115"
          src={bannerBg}
        />
        <div className="w-full h-full absolute top-0 left-0 px-[32px] py-[24px]">
          <div className="text-[#333] text-[20px] font-bold mb-[15px]">{title}</div>
          <div className="text-[#545E74] text-[16px]">{description}</div>
        </div>
      </div>

      {/* 教程横幅 */}
      {needsHelper && (
        <a
          className="w-[24%] h-[120px] relative block"
          href={helperLink}
          target={openNewTab ? '_blank' : ''}>
          <img
            alt=""
            className="w-full h-full object-cover rounded-[8px] contrast-115"
            src={helperBg}
          />
          <div className="w-full h-full absolute top-0 left-0 px-[32px] py-[24px]">
            <div className="text-[#333] text-[20px] font-bold mb-[15px]">教程</div>
            <div className="text-[#333] text-[14px]">{helperText}</div>
          </div>
        </a>
      )}
    </div>
  );
};

export default Banner;
