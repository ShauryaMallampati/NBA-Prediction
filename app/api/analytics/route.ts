import fs from "fs"
import { type NextRequest, NextResponse } from "next/server"
import path from "path"

export async function GET(request: NextRequest) {
  try {
    const projectRoot = process.cwd()
    
    // Try to read model metadata
    const modelMetaPath = path.join(projectRoot, "artifacts", "models", "pregame", "metadata.json")

    if (!fs.existsSync(modelMetaPath)) {
      return NextResponse.json({
        success: false,
        error: "Model metadata not found",
        message: "Train the pregame ensemble to generate artifacts/models/pregame/metadata.json.",
      }, { status: 404 })
    }

    const metaData = JSON.parse(fs.readFileSync(modelMetaPath, "utf-8"))
    const models = metaData.models || {}

    const modelMetrics = {
      ensemble_accuracy: null as number | null,
      cv_accuracy: typeof metaData.cv_accuracy === 'number' ? metaData.cv_accuracy : null,
      auc: null as number | null,
      models: {
        xgboost: { accuracy: null as number | null, auc: null as number | null },
        lightgbm: { accuracy: null as number | null, auc: null as number | null },
        catboost: { accuracy: null as number | null, auc: null as number | null }
      }
    }

    const accuracies = Object.values(models).map((m: any) => m?.accuracy).filter((v: any) => typeof v === 'number') as number[]
    const aucs = Object.values(models).map((m: any) => m?.auc).filter((v: any) => typeof v === 'number') as number[]

    if (accuracies.length > 0) {
      modelMetrics.ensemble_accuracy = accuracies.reduce((a, b) => a + b, 0) / accuracies.length
    }

    if (aucs.length > 0) {
      modelMetrics.auc = aucs.reduce((a, b) => a + b, 0) / aucs.length
    }

    if (models.xgboost) {
      modelMetrics.models.xgboost = {
        accuracy: typeof models.xgboost.accuracy === 'number' ? models.xgboost.accuracy : null,
        auc: typeof models.xgboost.auc === 'number' ? models.xgboost.auc : null,
      }
    }
    if (models.lightgbm) {
      modelMetrics.models.lightgbm = {
        accuracy: typeof models.lightgbm.accuracy === 'number' ? models.lightgbm.accuracy : null,
        auc: typeof models.lightgbm.auc === 'number' ? models.lightgbm.auc : null,
      }
    }
    if (models.catboost) {
      modelMetrics.models.catboost = {
        accuracy: typeof models.catboost.accuracy === 'number' ? models.catboost.accuracy : null,
        auc: typeof models.catboost.auc === 'number' ? models.catboost.auc : null,
      }
    }
    
    // Calculate additional metrics
    const response = {
      success: true,
      metrics: {
        overall: {
          training_accuracy: modelMetrics.ensemble_accuracy,
          cv_accuracy: modelMetrics.cv_accuracy,
          auc: modelMetrics.auc,
          calibration: typeof metaData.calibration === 'number' ? metaData.calibration : null,
        },
        by_model: {
          xgboost: modelMetrics.models.xgboost,
          lightgbm: modelMetrics.models.lightgbm,
          catboost: modelMetrics.models.catboost,
        },
        feature_importance: Array.isArray(metaData.feature_importance) ? metaData.feature_importance : [],
      },
      generated_at: metaData.generated_at || new Date().toISOString(),
      source: 'metadata',
    }
    
    return NextResponse.json(response)
  } catch (error) {
    console.error("Error fetching analytics:", error)
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch analytics",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    )
  }
}
