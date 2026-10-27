"""Local visual-only refinement of the installed custom boot twin generator output."""
from pathlib import Path
import subprocess
import re
r=Path(__file__).resolve().parents[1];p=r/'theme/omarchy-boot.script'
s=(r/'source/generated-upstream.script').read_text()
# Fixed Saga palette, independent of global theme configuration.
s=s.replace('fg.r = '+s.split('fg.r = ',1)[1].split('\n',1)[0], 'fg.r = 0.918; fg.g = 0.839; fg.b = 0.737;')
a=s.index('for (i = 0; i < 24 * display_count; i++) {');b=s.index('\n\nfun hide_bullets()',a)
s=s[:a]+'''for (d = 0; d < display_count; d++) {
  bs = Math.Int(ent_ih[d] * 0.39);
  if (bs < 8) bs = 8;
  bullet_scaled[d] = bullet.image.Scale(bs, bs);
  for (i = 0; i < 24; i++) {
    bullets[d * 24 + i] = Sprite(bullet_scaled[d]);
    bullets[d * 24 + i].SetOpacity(0);
  }
  label_image = Image("placeholder.png");
  label_h = ent_ih[d] * 0.58;
  labels[d] = Sprite(label_image.Scale(label_image.GetWidth() * label_h / label_image.GetHeight(), label_h));
  labels[d].SetPosition(ent_cx[d] - ent_iw[d] / 2, ent_cy[d] - label_h / 2, 6);
  labels[d].SetOpacity(0);
}''' + s[b:]
a=s.index('  if (count > 24) count = 24;');b=s.index('\n}\n\nfun display_normal_callback',a)
s=s[:a]+'''  # Only the bullet count is received. No key events or passphrase content.
  if (count < 0) count = 0;
  for (d = 0; d < display_count; d++) {
    step = bullet_scaled[d].GetWidth() + Math.Int(ent_ih[d] * 0.15);
    capacity = Math.Int(ent_iw[d] / step);
    if (capacity > 24) capacity = 24;
    if (capacity < 1) capacity = 1;
    shown = count;
    if (shown > capacity) shown = capacity;
    labels[d].SetOpacity(count == 0);
    x0 = ent_cx[d] - ent_iw[d] / 2;
    for (i = 0; i < 24; i++) {
      if (i < shown) {
        bullets[d * 24 + i].SetPosition(x0 + i * step, ent_cy[d] - bullet_scaled[d].GetHeight() / 2, 6);
        bullets[d * 24 + i].SetOpacity(1);
      } else bullets[d * 24 + i].SetOpacity(0);
    }
  }''' + s[b:]
s=s.replace('  hide_bullets();\n','  hide_bullets();\n  for (d = 0; d < display_count; d++) labels[d].SetOpacity(0);\n')
s=re.sub(r"dim.r = [^\n]+", "dim.r = 0.820; dim.g = 0.761; dim.b = 0.675;", s)
s=re.sub(r"Window.SetBackground(Top|Bottom)Color\([^\n]+", r"Window.SetBackground\1Color(0.051, 0.090, 0.106);", s)
p.write_text(s)
ini=r/'theme/omarchy-boot.plymouth'
ini.write_text(re.sub(r'ConsoleLogBackgroundColor=0x[0-9a-fA-F]+', 'ConsoleLogBackgroundColor=0x0d171b',ini.read_text()))
# Assets generated from vector geometry/text; no artwork is redrawn or generated.
subprocess.run(['magick','-size','32x32','xc:none','-stroke','#ead6bc','-strokewidth','1.6','-fill','#b0c6b090','-draw','path "M16,5 L24,16 L16,27 L8,16 Z"',str(r/'theme/dot.png')],check=True)
subprocess.run(['magick','-background','none','-fill','#d1c2ac','-font',subprocess.check_output(['fc-match','-f','%{file}','Noto Sans'],text=True),'-pointsize','26','label:Enter disk passphrase',str(r/'theme/placeholder.png')],check=True)
