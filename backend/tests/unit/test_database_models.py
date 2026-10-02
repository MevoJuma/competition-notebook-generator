import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models import (
    AuditLog,
    Competition,
    CompetitionAnalysis,
    CompetitionFile,
    CompetitionPlatform,
    CompetitionStatus,
    DatasetProfile,
    Experiment,
    FileCategory,
    ModelRun,
    Notebook,
    NotebookExecution,
    NotebookStatus,
    ProblemType,
)


@pytest_asyncio.fixture
async def test_db_session():
    """Isolated in-memory SQLite database session for model testing."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await test_engine.dispose()


@pytest.mark.asyncio
async def test_competition_full_lifecycle_and_cascade(test_db_session: AsyncSession):
    """Verify complete CRUD lifecycle, foreign key relationships, and cascade deletions."""
    # 1. Create Competition
    comp = Competition(
        title="Financial Inclusion in Africa",
        slug="financial-inclusion-africa",
        platform=CompetitionPlatform.ZINDI.value,
        status=CompetitionStatus.UPLOADED.value,
        description="Predict who is most likely to have a bank account.",
    )
    test_db_session.add(comp)
    await test_db_session.commit()
    await test_db_session.refresh(comp)

    assert comp.id is not None
    assert comp.created_at is not None

    # 2. Add CompetitionFile
    comp_file = CompetitionFile(
        competition_id=comp.id,
        filename="Train.csv",
        original_name="Train.csv",
        file_type="csv",
        category=FileCategory.TRAIN_DATA.value,
        file_size_bytes=1024 * 50,
        file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        storage_path="/tmp/Train.csv",
    )
    test_db_session.add(comp_file)
    await test_db_session.commit()
    await test_db_session.refresh(comp_file)

    assert comp_file.id is not None
    assert comp_file.competition_id == comp.id

    # 3. Add DatasetProfile
    profile = DatasetProfile(
        competition_id=comp.id,
        file_id=comp_file.id,
        dataset_name="Train.csv",
        role="train",
        row_count=23524,
        column_count=13,
        memory_bytes=3058120,
        schema_definition={"country": "string", "bank_account": "string", "age": "int64"},
        column_profiles={"bank_account": {"null_count": 0, "unique_count": 2}},
        sample_rows=[{"country": "Kenya", "bank_account": "Yes", "age": 24}],
    )
    test_db_session.add(profile)
    await test_db_session.commit()

    # 4. Add CompetitionAnalysis
    analysis = CompetitionAnalysis(
        competition_id=comp.id,
        problem_type=ProblemType.BINARY_CLASSIFICATION.value,
        target_column="bank_account",
        id_columns=["unique_id"],
        train_file_name="Train.csv",
        test_file_name="Test.csv",
        evaluation_metric="ROC-AUC",
        metric_direction="MAXIMIZE",
        validation_strategy="StratifiedKFold",
        cv_strategy_details={"n_splits": 5, "shuffle": True},
        submission_columns=["unique_id", "bank_account"],
        leakage_risks=["Avoid using unique_id as feature"],
        feature_engineering_plan=["Frequency encode country", "Bin age into quartiles"],
        recommended_models=["LightGBM", "CatBoost"],
        confidence_score=0.98,
        reasoning_summary={"target_reason": "bank_account absent in Test.csv"},
    )
    test_db_session.add(analysis)
    await test_db_session.commit()

    # 5. Add Experiment and ModelRun
    exp = Experiment(
        competition_id=comp.id,
        name="Baseline Comparison",
        best_cv_score=0.8842,
        best_model_name="LightGBM_Baseline",
    )
    test_db_session.add(exp)
    await test_db_session.commit()

    model_run = ModelRun(
        experiment_id=exp.id,
        model_family="lightgbm",
        model_name="LightGBM_Baseline",
        hyperparameters={"learning_rate": 0.05, "n_estimators": 500},
        cv_mean_score=0.8842,
        cv_std_score=0.0031,
        fold_scores=[0.881, 0.885, 0.886, 0.882, 0.887],
        train_time_seconds=2.45,
    )
    test_db_session.add(model_run)
    await test_db_session.commit()

    # 6. Add Notebook & Execution
    notebook = Notebook(
        competition_id=comp.id,
        version=1,
        status=NotebookStatus.VALIDATED.value,
        storage_path="/tmp/solution.ipynb",
        structure_manifest={"sections": 28},
        syntax_valid=True,
        execution_valid=True,
        submission_valid=True,
    )
    test_db_session.add(notebook)
    await test_db_session.commit()

    execution = NotebookExecution(
        notebook_id=notebook.id,
        execution_status="SUCCESS",
        cells_executed=28,
        total_cells=28,
        runtime_seconds=15.2,
        execution_log="All 28 cells executed successfully.",
    )
    test_db_session.add(execution)
    await test_db_session.commit()

    # 7. Add AuditLog
    log = AuditLog(
        competition_id=comp.id,
        stage="VALIDATION",
        message="Notebook passed all 28 cell AST and dry-run assertions.",
    )
    test_db_session.add(log)
    await test_db_session.commit()

    comp_id = comp.id

    # Expire session so selectin relationships are freshly loaded from the database
    test_db_session.expire_all()

    # Verify query with relationships loaded
    result = await test_db_session.execute(
        select(Competition).where(Competition.id == comp_id)
    )
    fetched_comp = result.scalar_one()
    assert len(fetched_comp.files) == 1
    assert len(fetched_comp.dataset_profiles) == 1
    assert fetched_comp.analysis is not None
    assert len(fetched_comp.experiments) == 1
    assert len(fetched_comp.notebooks) == 1
    assert len(fetched_comp.audit_logs) == 1

    # 8. Test Cascade Delete
    await test_db_session.delete(fetched_comp)
    await test_db_session.commit()

    # Verify orphan records are deleted
    files_check = await test_db_session.execute(select(CompetitionFile).where(CompetitionFile.competition_id == comp_id))
    assert len(files_check.scalars().all()) == 0

    profiles_check = await test_db_session.execute(select(DatasetProfile).where(DatasetProfile.competition_id == comp_id))
    assert len(profiles_check.scalars().all()) == 0

    analyses_check = await test_db_session.execute(select(CompetitionAnalysis).where(CompetitionAnalysis.competition_id == comp_id))
    assert len(analyses_check.scalars().all()) == 0

    exps_check = await test_db_session.execute(select(Experiment).where(Experiment.competition_id == comp_id))
    assert len(exps_check.scalars().all()) == 0

    notebooks_check = await test_db_session.execute(select(Notebook).where(Notebook.competition_id == comp_id))
    assert len(notebooks_check.scalars().all()) == 0
