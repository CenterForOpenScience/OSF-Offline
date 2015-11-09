#include "startscreen.h"
#include "ui_startscreen.h"

startscreen::startscreen(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::startscreen)
{
    ui->setupUi(this);
}

startscreen::~startscreen()
{
    delete ui;
}
