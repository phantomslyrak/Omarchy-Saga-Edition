#include <QGuiApplication>
#include <QQuickWindow>
#include <QQuickView>
#include <QQuickItem>
#include <QQmlContext>
#include <QQmlEngine>
#include <QStandardItemModel>
#include <QTimer>
#include <QFile>
#include <QImage>
#include <QTest>
#include <dlfcn.h>
static QQuickItem *root=nullptr,*input=nullptr,*mask=nullptr;
static int failures=0;
static QString out;
static void log(const QString&s){QFile f(out+"/rune-tests.txt");if(f.open(QIODevice::Append)){f.write(s.toUtf8());f.write("\n");}}
static void check(bool ok,const QString&s){log((ok?"PASS ":"FAIL ")+s);if(!ok)failures++;}
static QList<QQuickItem*> marks(QQuickItem*i){QList<QQuickItem*> r;for(auto c:i->childItems()){if(c->property("morph").isValid())r<<c;r<<marks(c);}return r;}
static void syncCheck(const QString&name){
 auto n=input->property("length").toInt(),c=input->property("cursorPosition").toInt(),cap=mask->property("capacity").toInt();
 int start=qMax(0,qMin(qMax(0,n-cap),qMax(0,c-cap+1)));
 check(mask->property("count").toInt()==n&&mask->property("caret").toInt()==c&&mask->property("viewportStart").toInt()==start&&mask->property("visibleCount").toInt()==qMin(n-start,cap),name);
}
static void shot(QQuickWindow*w,const QString&n){auto im=w->grabWindow();check(im.width()==2560&&im.height()==1600&&im.save(out+"/"+n+".png"),n);}
int QCoreApplication::exec(){
 out=QString::fromUtf8(qgetenv("SAGA_RUNE_OUTPUT"));
 QTimer::singleShot(600,[]{
  for(auto w:QGuiApplication::allWindows()){
   auto view=qobject_cast<QQuickView*>(w);if(!view)continue;
   if(!view->rootObject()||view->rootObject()->objectName()!="sagaRoot")continue;
   auto model=new QStandardItemModel(view);model->setItemRoleNames({{Qt::UserRole+1,"file"}});
   for(auto n:{"hyprland-uwsm.desktop","omarchy-saga.desktop"}){auto row=new QStandardItem;row->setData(QString(n),Qt::UserRole+1);model->appendRow(row);}
   view->rootContext()->setContextProperty("sessionModel",model);auto url=view->source();view->setSource(QUrl());view->setSource(url);root=view->rootObject();
   input=root->findChild<QQuickItem*>("sagaPassword");mask=root->findChild<QQuickItem*>("sagaRuneMask");
   check(input&&mask,"theme loads with rune overlay");if(!input||!mask){QCoreApplication::exit(2);return;}
   QTest::qWait(100);input->forceActiveFocus();
   check(input->property("echoMode").toInt()==2&&input->property("passwordMaskDelay").toInt()==0,"native Password echo mode; zero plaintext delay");
   check(input->property("color").value<QColor>().alpha()==0&&input->property("selectedTextColor").value<QColor>().alpha()==0,"native dots and selected text transparent");
   check(input->findChild<QQuickItem*>("sagaHiddenCursor") != nullptr,"native cursor uses empty nonpainting delegate");
   QTest::keyClick(view,Qt::Key_A);QTest::qWait(55);
   auto birth=marks(mask);check(!birth.empty()&&birth.first()->property("morph").toReal()<0.05,"new point precedes rune morph");auto pointImage=view->grabWindow();
   bool intermediate=false;QImage morphImage;
   for(int i=0;i<35;i++){QTest::qWait(10);auto mid=marks(mask);if(!mid.empty()){auto m=mid.first()->property("morph").toReal();if(m>0.05&&m<0.99){intermediate=true;morphImage=view->grabWindow();break;}}}
   check(intermediate,"intermediate dot-to-rune morph");
   pointImage.save(out+"/01-point-55ms.png");morphImage.save(out+"/02-morph.png");
   QTest::qWait(220);auto done=marks(mask);check(!done.empty()&&done.first()->property("morph").toReal()>0.99,"rune settles and persists");
   for(int i=0;i<5;i++)QTest::keyClick(view,Qt::Key_B);QTest::qWait(450);syncCheck("six positional rune variants aligned");shot(view,"03-six-runes");
   QTest::keyClick(view,Qt::Key_Backspace);QTest::qWait(10);QMetaObject::invokeMethod(root->findChild<QObject*>("runeStrip"),"forceLayout");QTest::qWait(55);syncCheck("Backspace updates count while removal animates");
   bool fading=false;for(auto i:marks(mask))if(i->property("ordinal").toInt()==5&&i->opacity()>0&&i->opacity()<1)fading=true;
   for(auto i:marks(mask))log(QString("remove observation ordinal=%1 opacity=%2 scale=%3").arg(i->property("ordinal").toInt()).arg(i->opacity()).arg(i->scale()));
   check(fading,"removed rune fades rather than vanishing instantly");shot(view,"04-backspace-fade");
   QTest::qWait(200);
   for(int i=0;i<90;i++)QTest::keyClick(view,Qt::Key_A);QTest::qWait(60);syncCheck("rapid 95-character input with bounded viewport");
   QTest::keyClick(view,Qt::Key_Home);QTest::qWait(45);syncCheck("Home viewport/caret");
   for(int i=0;i<3;i++)QTest::keyClick(view,Qt::Key_Right);QTest::keyClick(view,Qt::Key_C);QTest::qWait(45);syncCheck("middle insertion");
   QTest::keyClick(view,Qt::Key_Delete);QTest::qWait(45);syncCheck("middle deletion");
   QTest::keyClick(view,Qt::Key_End);QTest::qWait(45);syncCheck("End viewport/caret");
   for(int i=0;i<110;i++)QTest::keyClick(view,Qt::Key_Backspace);QTest::qWait(220);syncCheck("held-Backspace-equivalent repeated deletion reaches empty");check(mask->property("settledEmpty").toBool(),"empty placeholder resumes after fade");
   for(int i=0;i<12;i++)QTest::keyClick(view,Qt::Key_D);QTest::qWait(70);
   QTest::keyClick(view,Qt::Key_A,Qt::ControlModifier);QTest::keyClick(view,Qt::Key_E);QTest::qWait(60);syncCheck("select-all replacement");check(input->property("length").toInt()==1,"replacement length one");
   QTest::keyClick(view,Qt::Key_Return);check(root->property("busy").toBool(),"Enter uses existing SDDM submit handler");
   auto proxy=view->rootContext()->contextProperty("sddm").value<QObject*>();check(QMetaObject::invokeMethod(proxy,"loginFailed",Qt::DirectConnection),"greeter failure signal delivered");
   check(input->property("length").toInt()==0&&mask->property("visibleCount").toInt()==0&&!mask->isVisible()&&input->hasActiveFocus(),"failure immediately clears native input and visual slots; focus restored");
   QTest::keyClick(view,Qt::Key_F);QTest::qWait(450);syncCheck("typing immediately after failure stays aligned");shot(view,"05-retry-rune");
   QTest::keyClick(view,Qt::Key_Escape);QTest::qWait(220);syncCheck("Escape clears input and rune mask");
   check(root->property("sessionIndex").toInt()==1,"exact Saga session selection unchanged (fixture index 1)");
   log("FAILURES="+QString::number(failures));QCoreApplication::exit(failures?2:0);return;
  }
  log("FAIL theme root absent");QCoreApplication::exit(2);
 });
 auto original=reinterpret_cast<int(*)()>(dlsym(RTLD_NEXT,"_ZN16QCoreApplication4execEv"));return original();
}
