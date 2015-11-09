#ifndef STARTUP_H
#define STARTUP_H

#include <QMainWindow>

namespace Ui {
class StartUp;
}

class StartUp : public QMainWindow
{
    Q_OBJECT

public:
    explicit StartUp(QWidget *parent = 0);
    ~StartUp();

private:
    Ui::StartUp *ui;
};

#endif // STARTUP_H
