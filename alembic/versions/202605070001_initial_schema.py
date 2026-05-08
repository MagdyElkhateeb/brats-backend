"""Initial schema

Revision ID: 202605070001
Revises:
Create Date: 2026-05-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "202605070001"
down_revision = None
branch_labels = None
depends_on = None

case_status_enum = postgresql.ENUM(
    "CREATED", "PROCESSING", "COMPLETED", "FAILED", name="case_status", create_type=False
)
sequence_type_enum = postgresql.ENUM(
    "T1", "T1CE", "T2", "FLAIR", name="sequence_type", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    case_status_enum.create(bind, checkfirst=True)
    sequence_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("patient_code", sa.String(length=100), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "patient_code", name="uq_patient_user_code"),
    )
    op.create_index(op.f("ix_patients_id"), "patients", ["id"], unique=False)
    op.create_index(op.f("ix_patients_user_id"), "patients", ["user_id"], unique=False)

    op.create_table(
        "cases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("scan_date", sa.Date(), nullable=True),
        sa.Column("status", case_status_enum, server_default="CREATED", nullable=False),
        sa.Column("task_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cases_id"), "cases", ["id"], unique=False)
    op.create_index(op.f("ix_cases_patient_id"), "cases", ["patient_id"], unique=False)
    op.create_index(op.f("ix_cases_user_id"), "cases", ["user_id"], unique=False)

    op.create_table(
        "case_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("sequence_type", sequence_type_enum, nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "sequence_type", name="uq_case_file_sequence"),
    )
    op.create_index(op.f("ix_case_files_case_id"), "case_files", ["case_id"], unique=False)
    op.create_index(op.f("ix_case_files_id"), "case_files", ["id"], unique=False)

    op.create_table(
        "case_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("mask_url", sa.String(length=1024), nullable=True),
        sa.Column("slices_urls", sa.JSON(), nullable=False),
        sa.Column("overlays_urls", sa.JSON(), nullable=False),
        sa.Column("total_tumor_volume", sa.Float(), nullable=True),
        sa.Column("edema_volume", sa.Float(), nullable=True),
        sa.Column("enhancing_volume", sa.Float(), nullable=True),
        sa.Column("non_enhancing_volume", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_case_results_case_id"), "case_results", ["case_id"], unique=True)
    op.create_index(op.f("ix_case_results_id"), "case_results", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_case_results_id"), table_name="case_results")
    op.drop_index(op.f("ix_case_results_case_id"), table_name="case_results")
    op.drop_table("case_results")
    op.drop_index(op.f("ix_case_files_id"), table_name="case_files")
    op.drop_index(op.f("ix_case_files_case_id"), table_name="case_files")
    op.drop_table("case_files")
    op.drop_index(op.f("ix_cases_user_id"), table_name="cases")
    op.drop_index(op.f("ix_cases_patient_id"), table_name="cases")
    op.drop_index(op.f("ix_cases_id"), table_name="cases")
    op.drop_table("cases")
    op.drop_index(op.f("ix_patients_user_id"), table_name="patients")
    op.drop_index(op.f("ix_patients_id"), table_name="patients")
    op.drop_table("patients")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    sequence_type_enum.drop(bind, checkfirst=True)
    case_status_enum.drop(bind, checkfirst=True)
