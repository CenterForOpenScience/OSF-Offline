#include "preferences.h"
#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    Preferences w;
    w.show();
    
    return a.exec();
}
