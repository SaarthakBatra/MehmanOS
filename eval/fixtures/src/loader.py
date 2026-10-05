from datetime import date
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator, ConfigDict

ValidTools = Literal[
    "search_properties", 
    "check_availability", 
    "get_room_details", 
    "calculate_price", 
    "get_policy", 
    "create_booking_hold"
]
ValidActions = Literal["ask_question", "call_tool", "recommend", "hold"]
HallucinationDimension = Literal["price", "availability", "amenities", "policies"]

class BookingStateDelta(BaseModel):
    model_config = ConfigDict(extra='forbid')

    destination: Optional[str] = None
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    guests: Optional[int] = None
    budget_per_night: Optional[float] = None
    room_preference: Optional[str] = None
    special_requirements: Optional[List[str]] = None
    
    selected_property_id: Optional[str] = None
    selected_room_id: Optional[str] = None
    add_ons: Optional[List[str]] = None
    booking_hold_ref: Optional[str] = None

class Turn(BaseModel):
    user: str
    expected_state_delta: BookingStateDelta
    expected_tool_called: Optional[ValidTools] = None
    expected_next_action: ValidActions
    must_not_hallucinate: List[HallucinationDimension] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_coherence(self):
        if self.expected_next_action == "call_tool":
            assert self.expected_tool_called is not None, "If action is 'call_tool', expected_tool_called must be defined."
        else:
            assert self.expected_tool_called is None, f"If action is '{self.expected_next_action}', expected_tool_called must be None."
        return self

class EvaluationFixture(BaseModel):
    test_id: str
    description: str
    mock_current_date: date
    turns: List[Turn]

def load_properties() -> list[dict]:
    import json
    with open("data/properties/src/properties.json", "r") as f:
        return json.load(f)

def _read_json_files(fixtures_dir: str) -> list[dict]:
    import os, json
    json_data = []
    if not os.path.exists(fixtures_dir):
        raise FileNotFoundError(f"Directory {fixtures_dir} does not exist")
    files = os.listdir(fixtures_dir)
    if not files:
        raise FileNotFoundError("Directory is empty")
    for file in files:
        if file.endswith(".json"):
            with open(os.path.join(fixtures_dir, file), "r") as f:
                json_data.append(json.load(f))
    if not json_data:
        raise FileNotFoundError("No JSON files found")
    return json_data

def load_fixtures(fixtures_dir: str = "eval/fixtures/") -> list[EvaluationFixture]:
    from pydantic import ValidationError
    props = load_properties()
    valid_property_ids = {p["property_id"] for p in props if "property_id" in p}
    valid_room_ids = {r["room_id"] for p in props for r in p.get("room_types", []) if "room_id" in r}

    fixtures_data = _read_json_files(fixtures_dir)
    fixtures = []
    for data in fixtures_data:
        fixture = EvaluationFixture.model_validate(data)
        for turn in fixture.turns:
            delta = turn.expected_state_delta
            if delta.selected_property_id and delta.selected_property_id not in valid_property_ids:
                raise ValueError(f"Invalid property_id: {delta.selected_property_id}")
            if delta.selected_room_id and delta.selected_room_id not in valid_room_ids:
                raise ValueError(f"Invalid room_id: {delta.selected_room_id}")
        fixtures.append(fixture)
    return fixtures
