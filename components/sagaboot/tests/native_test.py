"""Actual installed Plymouth parser/interpreter with mock display, no daemon/input/device access."""
import ctypes as C
from pathlib import Path
r=Path(__file__).resolve().parents[1]
class Return(C.Structure): _fields_=[('type',C.c_int),('object',C.c_void_p)]
l=C.CDLL('/usr/lib/plymouth/script.so')
l.script_parse_string.argtypes=[C.c_char_p,C.c_char_p];l.script_parse_string.restype=C.c_void_p
l.script_state_new.argtypes=[C.c_void_p];l.script_state_new.restype=C.c_void_p
l.script_execute.argtypes=[C.c_void_p,C.c_void_p];l.script_execute.restype=Return
l.script_obj_as_number.argtypes=[C.c_void_p];l.script_obj_as_number.restype=C.c_double
l.script_obj_unref.argtypes=[C.c_void_p];l.script_state_destroy.argtypes=[C.c_void_p];l.script_parse_op_free.argtypes=[C.c_void_p]
prelude='''
fun MakeImage(w,h) {
 local.o.w=w; local.o.h=h;
 local.o.GetWidth=fun(){return this.w;};local.o.GetHeight=fun(){return this.h;};
 local.o.Scale=fun(w,h){return MakeImage(w,h);};return local.o;
}
fun Image(name) { if(name=="placeholder.png")return MakeImage(280,40);return MakeImage(2560,1600); }
Image = Image | [];
Image.Text=fun(text,r,g,b,a,font){return MakeImage(200,20);};
fun Sprite(img) {
 local.o.opacity=1;local.o.x=0;local.o.y=0;local.o.image=img;
 local.o.SetOpacity=fun(v){this.opacity=v;};
 local.o.SetImage=fun(img){this.image=img;};
 local.o.SetPosition=fun(x,y,z){this.x=x;this.y=y;this.z=z;};return local.o;
}
Window.GetWidth=fun(i){if(i==null||i<global.heads)return global.test_w;return 0;};
Window.GetHeight=fun(i){if(i==null||i<global.heads)return global.test_h;return 0;};
Window.SetX=fun(i,x){};Window.SetY=fun(i,y){};
Window.SetBackgroundTopColor=fun(r,g,b){};Window.SetBackgroundBottomColor=fun(r,g,b){};
Plymouth.GetMode=fun(){return global.test_mode;};
Plymouth.SetDisplayPasswordFunction=fun(f){global.password_cb=f;};
Plymouth.SetDisplayNormalFunction=fun(f){global.normal_cb=f;};
Plymouth.SetRefreshFunction=fun(f){global.refresh_cb=f;};
Plymouth.SetDisplayMessageFunction=fun(f){global.message_cb=f;};
Plymouth.SetHideMessageFunction=fun(f){global.hide_message_cb=f;};
Math.Int=fun(n){return n-n%1;};
'''
checks='''
global.failures=0;
fun check(ok){if(!ok)global.failures++;}
check(display_count==global.heads);
check(bg_sprites[0].opacity==1);
check(labels[0].opacity==0 && bullets[0].opacity==0);
global.password_cb("Public synthetic prompt",0);
check(labels[0].opacity==1 && global.boot_wait==0);
check(bg_sprites[0].opacity==1);
global.password_cb("Public synthetic prompt",1);
check(bullets[0].opacity==1 && bullets[1].opacity==0 && labels[0].opacity==0);
global.password_cb("Public synthetic prompt",8);
check(bullets[7].opacity==1 && bullets[8].opacity==0);
global.password_cb("Public synthetic prompt",3);
check(bullets[2].opacity==1 && bullets[3].opacity==0);
global.password_cb("Public synthetic prompt",256);
for(d=0;d<display_count;d++){
 for(i=0;i<24;i++)if(bullets[d*24+i].opacity==1){
  check(bullets[d*24+i].x>=ent_cx[d]-ent_iw[d]/2);
  check(bullets[d*24+i].x+bullet_scaled[d].GetWidth()<=ent_cx[d]+ent_iw[d]/2);
 }
}
global.password_cb("Public synthetic prompt",0);
check(bullets[0].opacity==0 && labels[0].opacity==1);
global.normal_cb();
check(global.boot_wait==1 && labels[0].opacity==0 && bullets[0].opacity==0);
global.refresh_cb();check(booting_sprites[0].opacity==1);
global.message_cb("Synthetic failure message");check(message_sprite.opacity==1);
global.password_cb("Public synthetic retry",0);
check(global.boot_wait==0 && booting_sprites[0].opacity==0 && labels[0].opacity==1);
global.hide_message_cb("Synthetic failure message");check(message_sprite.opacity==0);
return global.failures;
'''
script=(r/'theme/omarchy-boot.script').read_text()
for w,h,heads in [(2560,1600,1),(2048,1280,1),(1280,800,1),(1920,1080,2)]:
 text=f'global.test_w={w};global.test_h={h};global.heads={heads};global.test_mode="boot";\n'+prelude+script+checks
 op=l.script_parse_string(text.encode(),b'sagaboot-test');assert op,'parse failed'
 state=l.script_state_new(None);result=l.script_execute(state,op)
 assert result.type==1 and result.object,'script did not return test result'
 errors=l.script_obj_as_number(result.object)
 l.script_obj_unref(result.object);l.script_state_destroy(state);l.script_parse_op_free(op)
 if errors:
  for expression in ['bullets[0].x','ent_cx[0]','ent_iw[0]','bullet_scaled[0].GetWidth()','bullets[23].x']:
   probe=text.replace('return global.failures;', 'return '+expression+';')
   op=l.script_parse_string(probe.encode(),b'probe');state=l.script_state_new(None);ret=l.script_execute(state,op)
   print(expression,l.script_obj_as_number(ret.object));l.script_obj_unref(ret.object);l.script_state_destroy(state);l.script_parse_op_free(op)
 assert errors==0,(w,h,heads,errors)
 print(f'NATIVE_CALLBACK_TEST_PASS {w}x{h} heads={heads}')

# Negative control: prove the bounds checks catch an oversized unbounded mask.
mutated=script.replace('if (shown > capacity) shown = capacity;', 'shown = count;')
text='global.test_w=1280;global.test_h=800;global.heads=1;global.test_mode="boot";\n'+prelude+mutated+checks
op=l.script_parse_string(text.encode(),b'negative-control');assert op
state=l.script_state_new(None);ret=l.script_execute(state,op)
assert ret.type==1 and l.script_obj_as_number(ret.object)>0,'bounds checks failed to detect broken mask'
l.script_obj_unref(ret.object);l.script_state_destroy(state);l.script_parse_op_free(op)
print('NEGATIVE_CONTROL_PASS: unbounded mask rejected')
