## Datasets
This folder contains the datasets we collected and used in our experiments.

### Dataset Structure
The input to the automated pipeline follows the following data structure:
```json
{
    "modelName": "car",
    "modelDesc": "We would like to model a car in this system, which involves the interaction between owners, car door, the key, and the engine.",
    "interactionMode": "interleaving",
    "subsystemCount": 4,
    "subsystems": [
        ...,
        {
            "name": "motor",
            "description": "This process models the motor in the car. The engine can be turned on and off, the car can start and stop driving, the fuel is gradually consumed after driving, and it can be refueled."
        }
    ],
    "assertions": [
        {
            "assertionType": "deadlock-free",
            "component": "",
            "stateName": "",
            "reachabilityType": "state",
            "customDescription": "",
            "conditions": [
                {
                "variable": "",
                "value": "",
                "connector": "AND"
                }
            ],
            "editingFinished": false,
            "assertionTruth": "",
            "ltlLogic": "",
            "ltlTarget": "",
            "selectedActions": []
        }
    ]
}
```

### Running Experiments on Custom Datasets
If you would like to run experiments on a different dataset, please organize the information for each system following the data structure discussed above.