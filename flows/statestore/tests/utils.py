from flows.statestore.tests.models import TestModel


def store_state_works(case, store):
    
    test_model = TestModel.objects.create(fruit='apple', count=34)
    
    task_id = '10293847565647382910abdcef1029384756'
    
    state = {'a': 1,
             'b': 'cake',
             'model': test_model,
             'pies': {'r': 2, 'theta': 20 }
             }
    
    store.put_state(task_id, state)
    
    fetched_state = store.get_state(task_id)
    
    case.assertTrue('a' in fetched_state)
    case.assertEqual(1, fetched_state['a'])
    
    case.assertTrue('b' in fetched_state)
    case.assertEqual('cake', fetched_state['b'])
    
    case.assertTrue('model' in fetched_state)
    fetched_model = fetched_state['model']
    case.assertEqual(test_model.id, fetched_model.id)
    case.assertEqual(test_model.fruit, fetched_model.fruit)
    case.assertEqual(test_model.count, fetched_model.count)
    
    case.assertTrue('pies' in fetched_state)
    case.assertEqual({'r': 2, 'theta': 20 }, fetched_state['pies'])
