import pymongo
from bson.json_util import loads, dumps
import json
import traceback
import pandas as pd
import os
from urllib.parse import quote

from .excel_export import documents_to_dataframe

class MongoDB:
    def __init__(self, collection: str, scoring_aggregation: list, address = "10.30.0.2:27017"):
        uri = "mongodb://" + quote(os.getenv("MONGO_INITDB_ROOT_USERNAME")) + ":" + quote(os.getenv("MONGO_INITDB_ROOT_PASSWORD")) + "@" + address + "/"
        self.client = pymongo.MongoClient(uri)
        self.db = self.client["billard"]

        self.col_name = collection
        try:
            self.collection = self.db[collection]
        except Exception as e:
            print("Error while getting (or creating, if not previously existing) the collection from the MongoDB, most likely an invalid collection name")
            raise e

        self.agg = scoring_aggregation

        self.last_insertion = None

    def assert_aggregation(self, agg, match={}):
        """Check if an aggregation works and creates the expected value.

        Args:
            agg (dict): mongoDB aggregation
            match (dict, optional): Extra stage to filter documents before sampling all documents to test the aggregation. Defaults to {}.

        Returns:
            bool, bool, str: If the check passed, if there are any documents returned from the agg, message describing the result.
        """
        # get a random document to test the aggregation on
        aggCursor = self.collection.aggregate([
            {"$match": match}, 
            {"$sample": {"size": 1}}
        ])
        samples = [d for d in aggCursor]
        if len(samples) == 0:
            text = f"The collection {self.col_name} has no entries yet. We assume this to be the setup of a gamemode, so the aggregation cant be checked and is assumed to work.\nThis aggregation will be saved and applied.\nPlay a round of the gamemode (saving the history) and then reenter the same aggregation so it will get checked.\nIf there is an error during the saving of the history, this means your aggregation has an error."
            print(text)
            return True, False, text
        sample = samples[0]
        try:
            score = self.get_score(_id=sample["_id"], insert=False, new_agg=agg)
            text = f"The document \n\n{sample}\n\nwas used to calculate a score of {score}."
            print(text)
            return True, True, text
        except Exception:
            text = "The aggregation caused an error. Correct your formula by reading the following stack trace from MongoDB\n\n" + traceback.format_exc() + f"\n\nThe document this was tried on was:\n{sample}"
            print(text)
            return False, False, text
            

    def enter_round(self, history: dict):
        """Enters a round into the 

        Args:
            history (dict): _description_

        Returns:
            _type_: _description_
        """
        # hash the item so we can compare it against already existing entries
        item_hash = self._hash_item(history)
        history["_item_hash"] = item_hash
        
        # overwrite if there was a previously existing document
        ret = self.collection.replace_one({"_item_hash": item_hash}, history, upsert=True)
        if ret.matched_count > 0:
            # if there was a match, just return the _id instead of actually inserting a new one
            matches = self.select_items({"_item_hash": item_hash})
            _id = matches[0]["_id"]
        else:
            _id = ret.upserted_id

        self.last_insertion = _id
        return _id

    def get_score(self, _id="latest", insert=True, new_agg=False, match={}):
        if _id == "latest":
            #assert self.last_insertion != None, "There was no entry inserted in this process. Cant calculate score."
            if self.last_insertion is None:
                return 0
            _id = self.last_insertion

        agg = [{"$match": match}] + (new_agg if new_agg else self.agg)

        #if _id != "all":
        #    agg = [{"$match": {"_id": _id}}] + agg

        aggCursor = self.collection.aggregate(agg)

        results = [document for document in aggCursor]
        #assert len(results) == 1 or _id == "all", f"There where {len(results)} documents for the given _id={_id}, where exactly 1 was expected"

        trace = "\n".join([line.strip() for line in traceback.format_stack()])

        print("GET SCORE CALLED ON DOCUMENTS:", "\n".join([str(r["_id"]) for r in results]), "\nusing agg", agg, "\n\n", trace)

        if insert:
            for result in results:
                # this is not the most efficient, but it works and lets the insertion be optional
                self.collection.update_one({"_id": result["_id"]}, {"$set": {"score": result["score"]}})
        
        scores = [r["score"] for r in results if r["_id"] == _id]
        return scores[0] if len(scores) > 0 else None
        #return results[0]["score"] # only relevant when getting one score

    def select_items(self, query={}):
        return [x for x in self.collection.find(query)]

    def aggregate(self, query: list):
        return [x for x in self.collection.aggregate(query)]


    def _hash_item(self, item: dict):
        # dump to str using bson insteada of json serializer
        st = dumps({k: v for k,v in item.items() if k not in ["_item_hash", "timestamp", "score"]}, sort_keys=True)
        hs = hash(st)
        return hs

    def get_df(self):
        docs = list(self.collection.find({}, {"_id": 0, "_item_hash": 0}))

        df = documents_to_dataframe(docs)
        return df

if __name__=="__main__":
    m = MongoDB("KP2", 
        [
            {
                "$project": {
                    "score": {
                        "$subtract": [
                            {"$max": "$distance.distance"},
                            {"$multiply": [{"$min": "$precision.distance"}, 3]}
                        ]
                    }
                }
            }
        ],
        address="mongodb://localhost:27017/"
    )
    _id = m.enter_round({
        "player": "Mathis",
        "team": "isem-dev",
        "distance": [
            {"distance": 1234, "collisions": 3},
            {"distance": 1345, "collisions": 2},
        ],
        "precision": [
            {"distance": 23},
            {"distance": 143}
        ]
    })
    print("Entered _id=", _id)

    print(m.get_score())


    print("Done!")