"""Align Explorer Project header to the actual adjacent editor-tabs bottom.

The V4 host's many legacy layout layers may modify physical tab height and
top offset. Never assume that 'height:43px' means the rows align.
The original .tree-title.pynix-project-header used a more-specific
!important selector that once pinned the header to 31px. New height rules
must match or exceed its selector specificity.
"""

PROJECT_HEADER_SYNC_STYLE = """<style id="pynix-project-header-alignment">
.workspace-mode .tree .tree-title.pynix-project-header{
 box-sizing:border-box!important;
 height:var(--pynix-project-header-height,43px)!important;
 min-height:var(--pynix-project-header-height,43px)!important;
 max-height:var(--pynix-project-header-height,43px)!important;
 flex:0 0 var(--pynix-project-header-height,43px)!important;
 position:sticky!important;top:0!important;z-index:35!important;
 margin:0!important;display:flex!important;align-items:center!important;
 background:#1e1f22!important;border-bottom:1px solid #34363c!important;
}
.workspace-mode .tree{
 scroll-padding-top:var(--pynix-project-header-height,43px)!important;
}
</style>"""

PROJECT_HEADER_SYNC_SCRIPT = r"""<script id="pynix-project-header-measure">
(() => {
 const tree=document.querySelector('.workspace-mode .tree');
 const tabs=document.querySelector('.workspace-mode .editor-tabs');
 if(!tree||!tabs)return;
 let last=NaN;
 const sync=()=>{
  const left=tree.getBoundingClientRect();
  const right=tabs.getBoundingClientRect();
  if(left.height<=0||right.height<=0)return;
  // Align BOTTOM edges in screen space; CSS 43px alone did not do this
  // because the tree and editor live in different shell layouts.
  const height=Math.max(43,Math.min(120,right.bottom-left.top));
  if(!Number.isFinite(height))return;
  if(Number.isFinite(last)&&Math.abs(last-height)<0.5)return;
  last=height;
  tree.style.setProperty('--pynix-project-header-height',height+'px');
 };
 const observer=new ResizeObserver(sync);
 observer.observe(tree);
 observer.observe(tabs);
 window.addEventListener('resize',sync);
 requestAnimationFrame(sync);
})();
</script>"""


def apply_project_header_alignment(document: str) -> str:
    """Inject once, after all historical shell CSS, using actual tab geometry."""
    if "</body>" not in document or 'id="pynix-project-header-measure"' in document:
        return document
    return document.replace(
        "</body>", PROJECT_HEADER_SYNC_STYLE + PROJECT_HEADER_SYNC_SCRIPT + "</body>", 1
    )
