import uvicorn
from fastapi import FastAPI, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from keras.models import load_model
from app.src.services.users import user_router, schemas, crud
from app.src.db.db import get_db
import warnings
from app.src.util.helper.preprocessor import preprocess_image
from fastapi import FastAPI

warnings.filterwarnings("ignore")

fastapp = FastAPI()
model = load_model("app/src/machine_learning_models/my_model.h5")


@fastapp.get("/ping")
async def health():
    return {"ping": "pong"}


@fastapp.post("/check_drowsiness")
async def check_drowsiness(
    request: schemas.drowsiness,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    image = preprocess_image(request.image)
    if type(image) == dict:
        if image["detail"] == "face not found":
            return JSONResponse(
                content={
                    "message": "Please keep your face in front of the camera",
                    "status": "face_not_found",
                }
            )
        if image["detail"] == "landmarks not configurable":
            return JSONResponse(
                content={
                    "message": "Please align your face in camera view",
                    "status": "align_face",
                }
            )
    image = image / 255.0
    image = image.reshape(1, 145, 145, 3)
    predictions = model.predict(image)
    background_tasks.add_task(
        crud.update_trip_frames_and_score, request.trip_id, predictions[0][0], db
    )
    if predictions[0][0] > 0.5:
        return JSONResponse(
            content={"message": "Not Sleeping", "status": "is_not_sleeping"}
        )
    else:
        return JSONResponse(
            content={
                "message": "Hey dont sleep you are driving",
                "status": "is_sleeping",
            }
        )


fastapp.include_router(user_router.router)
