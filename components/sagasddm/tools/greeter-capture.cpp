#include <QGuiApplication>
#include <QQuickWindow>
#include <QQuickItem>
#include <QQmlContext>
#include <QQmlEngine>
#include <QAbstractItemModel>
#include <QTimer>
#include <QFile>
#include <QImage>
#include <QTest>
#include <QStandardItemModel>
#include <QQuickView>
#include <dlfcn.h>
static QQuickItem *root = nullptr;
static void log(const QString &s) { QFile f(qgetenv("SAGA_REPORT")); if(f.open(QIODevice::Append)) {f.write(s.toUtf8());f.write("\n");} }
int QCoreApplication::exec() {
    QTimer::singleShot(800, [] {
        for (auto w : QGuiApplication::allWindows()) {
            auto qw=qobject_cast<QQuickWindow*>(w); if(!qw) continue;
            for(auto i: qw->contentItem()->childItems()) if(i->objectName()=="sagaRoot") root=i;
            if(!root) continue;
            qw->resize(2048,1280);
            auto context=QQmlEngine::contextForObject(root);
            for (auto name : {"sessionModel", "userModel"}) {
                auto m=qobject_cast<QAbstractItemModel*>(context->contextProperty(name).value<QObject*>());
                if(!m) {log(QString(name)+" missing");continue;}
                log(QString(name)+" rows="+QString::number(m->rowCount()));
                for(int i=0;i<m->rowCount();i++) for(auto role:m->roleNames().keys()) log(QString::number(i)+" "+m->roleNames()[role]+"="+m->data(m->index(i,0),role).toString());
            }
            if(qEnvironmentVariableIsSet("SAGA_FIXTURE")) {
                auto model=new QStandardItemModel(qw);
                model->setItemRoleNames({{Qt::UserRole+1,"file"}});
                for(auto name : {"hyprland-uwsm.desktop", "omarchy-saga.desktop"}) {
                    auto row=new QStandardItem(); row->setData(QString(name),Qt::UserRole+1); model->appendRow(row);
                }
                auto view=qobject_cast<QQuickView*>(qw);
                view->rootContext()->setContextProperty("sessionModel",model);
                auto url=view->source(); view->setSource(QUrl()); view->setSource(url); root=view->rootObject();
                log("FIXTURE: only sessionModel replaced; real SDDM userModel/proxy and theme retained");
            }
            log("selected="+root->property("sessionIndex").toString());
            QTimer::singleShot(600,[qw] {
                auto img=qw->grabWindow(); log(QString("image=%1x%2 saved=%3").arg(img.width()).arg(img.height()).arg(img.save(QString::fromUtf8(qgetenv("SAGA_CAPTURE")))));
                auto p=root->findChild<QQuickItem*>("sagaPassword");
                log("passwordFocus="+QString::number(p && p->hasActiveFocus()));
                if(p) {
                    p->forceActiveFocus();
                    for(int i=0;i<4;i++) QTest::keyClick(qw,Qt::Key_A);
                    log("typedLength="+p->property("length").toString());
                    QTest::keyClick(qw,Qt::Key_Escape);
                    log("escapeLength="+p->property("length").toString());
                    QTest::keyClick(qw,Qt::Key_Tab);
                    log("tabMoved="+QString::number(!p->hasActiveFocus()));
                    QTest::keyClick(qw,Qt::Key_Backtab);
                    log("backtabFocus="+QString::number(p->hasActiveFocus()));
                    QTest::keyClick(qw,Qt::Key_Return);
                    log("enterBusy="+root->property("busy").toString());
                    auto proxy=QQmlEngine::contextForObject(root)->contextProperty("sddm").value<QObject*>();
                    bool ok=QMetaObject::invokeMethod(proxy,"loginFailed",Qt::DirectConnection);
                    log(QString("failureSignal=%1 busy=%2 failed=%3 focus=%4 empty=%5").arg(ok).arg(root->property("busy").toBool()).arg(root->property("failed").toBool()).arg(p->hasActiveFocus()).arg(p->property("length").toInt()==0));
                }
                QCoreApplication::quit();
            });
        }
        if(!root) { log("NO THEME ROOT"); QCoreApplication::quit(); }
    });
    auto original=reinterpret_cast<int(*)()>(dlsym(RTLD_NEXT,"_ZN16QCoreApplication4execEv"));
    return original();
}
