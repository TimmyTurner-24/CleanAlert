import os

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for, current_app
from flask_login import current_user

from .. import db
from ..models import Report
from .forms import ReportForm, UpdateReportStatus
from ..users.utils import admin_required, resident_required, save_picture

reports = Blueprint('reports',__name__)

@reports.route("/report", methods=['GET', 'POST'])
@resident_required
def make_report():
    form = ReportForm()
    if form.validate_on_submit():
        upload_file = ''
        if form.upload.data:
            upload_file = save_picture(form.upload.data, 'static/uploads')
        report = Report(category=form.category.data, description=form.description.data, location=form.location.data, img=upload_file, author=current_user)
        db.session.add(report)
        db.session.commit()
        flash('Your complaint has been sent!', 'success')
        return redirect(url_for('reports.view_reports'))
    elif request.method == 'GET':
        form.description.data = 'Exactly as category'
    return render_template('Resident/mk_report.html', title='Make Report', form=form)

@reports.route("/report/<int:report_id>", methods=['GET', 'POST'])
@resident_required
def update_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.author != current_user or report.status != 'pending':
        abort(404)
    form = ReportForm()
    if form.validate_on_submit():
        report.category = form.category.data
        report.description = form.description.data
        report.location = form.location.data
        if form.upload.data:
            if report.img:
                rm_pic_path = os.path.join(current_app.root_path, 'static/uploads', report.img)
                os.remove(rm_pic_path)
            report.img = save_picture(form.upload.data, 'static/uploads')
        db.session.commit()
        flash('Your report has been updated', 'success')
        return redirect(url_for('reports.view_reports'))
    elif request.method == 'GET':
        form.category.data = report.category
        form.description.data = report.description
        form.location.data = report.location
    return render_template('Resident/mk_report.html', title='Update Report', form=form)

@reports.route("/my-reports")
@resident_required
def view_reports():
    page = request.args.get('page', 1, type=int)
    reports = Report.query.filter_by(author=current_user).order_by(Report.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('Resident/view_report.html', title='My Reports', reports=reports)

@reports.route("/report/<int:report_id>/delete", methods=['POST'])
@resident_required
def delete_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.author != current_user:
        abort(403)
    if report.img:
        rm_pic_path = os.path.join(current_app.root_path, 'static/uploads', report.img)
        os.remove(rm_pic_path)
    db.session.delete(report)
    db.session.commit()
    flash('Your report has been deleted', 'success')
    return redirect(url_for('reports.view_reports'))

@reports.route("/admin/update-report/<int:report_id>", methods=['GET', 'POST'])
@admin_required
def update_status(report_id):
    report = Report.query.get_or_404(report_id)
    form = UpdateReportStatus()
    if form.validate_on_submit():
        report.status = form.status.data
        db.session.commit()
        flash('The report status has been updated!', 'success')
        return redirect(url_for('reports.admin_report_view'))
    return render_template('Admin/update_status_report.html', title='View all residents reports', report=report, form=form)

@reports.route("/admin/reports")
@admin_required
def admin_report_view():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', None)  # get filter from URL
    if status:
        # Filter by status
        reports = Report.query.filter_by(status=status).order_by(Report.date_posted.desc()).paginate(page=page, per_page=10)
    else:
        # Show all reports
        reports = Report.query.order_by(Report.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('Admin/report_stats.html', title='All Reports', reports=reports, current_status=status)