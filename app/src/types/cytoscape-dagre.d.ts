/**
 * GraphForge — TypeScript declaration for cytoscape-dagre
 * GraphForge — cytoscape-dagre 的 TypeScript 类型声明
 *
 * The `cytoscape-dagre` package does not ship its own TypeScript type
 * definitions. This module augmentation declares the ambient module so that
 * importing and registering the extension compiles without errors.
 *
 * `cytoscape-dagre` 包不包含自带的 TypeScript 类型定义。
 * 此模块补充声明了 ambient module，使得导入并注册该扩展时能够通过类型检查。
 *
 * Usage / 使用方式:
 *   import cytoscape from 'cytoscape'
 *   import dagre from 'cytoscape-dagre'
 *   cytoscape.use(dagre)
 *
 * @see https://github.com/cytoscape/cytoscape.js-dagre
 */
declare module 'cytoscape-dagre' {
  import cytoscape from 'cytoscape'

  /**
   * The dagre layout extension conforms to `cytoscape.Extention` (note the
   * original typo in the Cytoscape type definitions — "Extention" is the
   * canonical spelling used in @types/cytoscape).
   *
   * dagre 布局扩展符合 `cytoscape.Extention` 接口（注意 @types/cytoscape
   * 中保留了原拼写 "Extention" 作为规范名称）。
   */
  const dagre: cytoscape.Extention

  export default dagre
}
