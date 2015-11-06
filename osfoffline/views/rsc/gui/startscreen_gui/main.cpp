#include "startscreen.h"
#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    startscreen w;
    w.show();

    return a.exec();
}
