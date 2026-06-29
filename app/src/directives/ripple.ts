/**
 * Ripple Effect Directive (水波纹点击反馈指令)
 * =============================================
 *
 * This directive implements the Material Design ripple effect for clickable elements.
 * When a user clicks on an element with the v-ripple directive, a circular ripple
 * animation emanates from the click point, providing tactile visual feedback.
 *
 * 本指令实现了 Material Design 风格的水波纹点击反馈效果。
 * 当用户点击带有 v-ripple 指令的元素时，一个圆形波纹动画会从点击位置扩散，
 * 提供直观的触觉视觉反馈。
 *
 * Usage / 使用方式:
 *   <n-button v-ripple>Click me</n-button>             // Default ripple (golden) / 默认金色波纹
 *   <n-button v-ripple:light>Light theme</n-button>     // Light ripple (white) / 浅色白色波纹
 *   <n-button v-ripple.light>Light via modifier</n-button> // Alternative light syntax
 *
 * CSS Animation Requirement / CSS 动画要求:
 *   The ripple relies on a keyframe animation named `ripple-effect` defined in the
 *   global stylesheet. Ensure the following is included:
 *   水波纹效果依赖于全局样式表中定义的 `ripple-effect` 关键帧动画，请确保包含以下样式：
 *
 *   @keyframes ripple-effect {
 *     to { transform: scale(4); opacity: 0; }
 *   }
 *
 * Dependencies / 依赖:
 *   - Vue 3 Directive API (mounted / unmounted lifecycle hooks)
 */

import type { Directive } from 'vue'

/**
 * Extended HTMLElement interface to store the ripple event handler reference.
 * 扩展 HTMLElement 接口，用于保存波纹事件处理器的引用。
 *
 * Storing the handler reference on the element itself allows proper cleanup
 * during the unmounted lifecycle hook, preventing memory leaks.
 * 在元素自身保存事件处理器的引用，以便在卸载生命周期钩子中正确清理，防止内存泄漏。
 */
interface RippleElement extends HTMLElement {
  /** Stored reference to the bound click handler, used for cleanup / 绑定的点击处理器引用，用于清理 */
  _rippleHandler?: (e: MouseEvent) => void
}

/**
 * Creates and animates a ripple element at the click position.
 * 在点击位置创建并动画化一个水波纹元素。
 *
 * The function calculates the ripple size based on the element's bounding box,
 * ensuring the ripple is large enough to cover the entire element as it scales.
 * The ripple element is appended to the target element and self-removes when
 * the animation completes.
 *
 * 该函数根据元素的边界框计算波纹尺寸，确保波纹在缩放时足以覆盖整个元素。
 * 波纹元素被追加到目标元素中，并在动画完成后自动移除。
 *
 * @param event - The mouse click event, used to determine click position / 鼠标点击事件，用于确定点击位置
 * @param el - The target DOM element hosting the ripple / 承载波纹的目标 DOM 元素
 * @param light - If true, uses a white semi-transparent ripple for dark backgrounds
 *                如果为 true，使用白色半透明波纹，适用于深色背景
 */
function createRipple(event: MouseEvent, el: RippleElement, light = false) {
  // Get the element's bounding rectangle relative to the viewport
  // 获取元素相对于视口的边界矩形
  const rect = el.getBoundingClientRect()

  // Calculate ripple diameter: twice the larger dimension ensures full coverage
  // during the scale(4) animation transform
  // 计算波纹直径：取较大尺寸的两倍，确保在 scale(4) 动画变换过程中完全覆盖
  const size = Math.max(rect.width, rect.height) * 2

  // Center the ripple on the click point, offset by half the ripple size
  // 将波纹中心定位在点击点，偏移半个波纹尺寸
  const x = event.clientX - rect.left - size / 2
  const y = event.clientY - rect.top - size / 2

  // Create the ripple span element with inline styles
  // 创建波纹 span 元素并设置内联样式
  const ripple = document.createElement('span')
  ripple.className = 'v-ripple-inner'
  ripple.style.cssText = `
    position: absolute;
    border-radius: 50%;
    width: ${size}px;
    height: ${size}px;
    left: ${x}px;
    top: ${y}px;
    pointer-events: none;
    background: ${light ? 'rgba(255,255,255,0.4)' : 'rgba(194,164,116,0.3)'};
    animation: ripple-effect 0.7s ease-out forwards;
    z-index: 0;
  `

  // Ensure the element has a positioning context and overflow hidden for the ripple
  // 确保元素具有定位上下文和溢出隐藏以容纳波纹
  el.style.position = el.style.position || 'relative'
  el.style.overflow = el.style.overflow || 'hidden'

  // Append the ripple to the target element
  // 将波纹追加到目标元素
  el.appendChild(ripple)

  // Automatically remove the ripple element once the animation finishes
  // This prevents DOM element accumulation over time
  // 动画结束后自动移除波纹元素，防止 DOM 元素随时间累积
  ripple.addEventListener('animationend', () => {
    ripple.remove()
  })
}

/**
 * vRipple Directive
 * ===================
 *
 * A custom Vue 3 directive that adds Material Design ripple effect to elements.
 * 自定义 Vue 3 指令，为元素添加 Material Design 水波纹效果。
 *
 * Lifecycle / 生命周期:
 *   - mounted:   Attaches the click handler and sets cursor style
 *                绑定点击处理器并设置光标样式
 *   - unmounted: Removes the click handler to prevent memory leaks
 *                移除点击处理器以防止内存泄漏
 *
 * Modifiers / 修饰符:
 *   - .light or :arg="light": Use white ripple color for dark surfaces
 *                              使用白色波纹，适用于深色背景
 */
export const vRipple: Directive<RippleElement> = {

  /**
   * Directive mounted lifecycle hook.
   * 指令的 mounted 生命周期钩子。
   *
   * Creates a click handler with the appropriate ripple color and attaches it
   * to the element. The handler reference is stored on the element for later cleanup.
   *
   * 创建具有适当波纹颜色的点击处理器并将其绑定到元素上。
   * 处理器引用被存储在元素上以便后续清理。
   *
   * @param el - The element the directive is bound to / 指令绑定的元素
   * @param binding - Binding object containing arg and modifiers / 包含 arg 和修饰符的绑定对象
   */
  mounted(el: RippleElement, binding) {
    // Determine if light mode is enabled via arg (v-ripple:light) or modifier (v-ripple.light)
    // 通过 arg (v-ripple:light) 或修饰符 (v-ripple.light) 判断是否启用浅色模式
    const light = binding.arg === 'light' || binding.modifiers?.light

    // Create the click handler bound to this specific element and light setting
    // 创建绑定到此特定元素和浅色设置的点击处理器
    const handler = (e: MouseEvent) => createRipple(e, el, light)

    // Store handler reference for cleanup in unmounted
    // 保存处理器引用以便在 unmounted 中清理
    el._rippleHandler = handler
    el.addEventListener('click', handler)

    // Visual indicator that the element is interactive
    // 视觉提示，表明该元素是可交互的
    el.style.cursor = 'pointer'
  },

  /**
   * Directive unmounted lifecycle hook.
   * 指令的 unmounted 生命周期钩子。
   *
   * Removes the previously attached click handler to prevent memory leaks
   * when the directive's host element is destroyed.
   *
   * 移除先前绑定的点击处理器，防止在指令宿主元素销毁时发生内存泄漏。
   *
   * @param el - The element the directive was bound to / 指令绑定的元素
   */
  unmounted(el: RippleElement) {
    if (el._rippleHandler) {
      el.removeEventListener('click', el._rippleHandler)
      // Clean up the reference to allow garbage collection
      // 清理引用以允许垃圾回收
      delete el._rippleHandler
    }
  },
}
