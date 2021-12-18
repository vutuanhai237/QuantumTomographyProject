import qiskit
import numpy as np
import sys
import multiprocessing
sys.path.insert(1, '../')
import qtm.base, qtm.constant, qtm.nqubit, qtm.fubini_study, qtm.encoding
import importlib
importlib.reload(qtm.base)
importlib.reload(qtm.constant)
importlib.reload(qtm.onequbit)
importlib.reload(qtm.nqubit)
# Init parameters

# For arbitrary initial state

theta = np.pi/3

def run_ghz(num_layers, num_qubits):
    # GHZ

    thetas = np.random.random((num_qubits*5 - 4)*num_layers)

    qc = qiskit.QuantumCircuit(num_qubits, num_qubits)

    loss_values_ghz = []
    thetass_ghz = []
    for i in range(0, 2):
        # fubini_study for binho_state is same for koczor state
        
        print('GHZ (' + str(num_layers) + ' layer): ', i)
        G = qtm.fubini_study.calculate_alternative_layered_state(qc.copy(), thetas, num_layers)
        grad_loss = qtm.base.grad_loss(
            qc, 
            qtm.nqubit.create_GHZchecker_alternating_layered,
            thetas, r = 1/2, s = np.pi/2, num_layers = num_layers, theta = theta)
        thetas = np.real(thetas - qtm.constant.learning_rate*(np.linalg.inv(G) @ grad_loss)) 
        qc_copy = qtm.nqubit.create_GHZchecker_alternating_layered(qc.copy(), thetas, num_layers, theta)  
        loss = qtm.base.loss_basis(qtm.base.measure(qc_copy, list(range(qc_copy.num_qubits))))
        loss_values_ghz.append(loss)
        thetass_ghz.append(thetas)
    traces_ghz, fidelities_ghz = [], []
    for thetas in thetass_ghz:
        # Get |psi> = U_gen|000...>
        qc = qiskit.QuantumCircuit(num_qubits, num_qubits)
        qc = qtm.nqubit.create_alternating_layerd_state(qc, thetas, num_layers = num_layers)
        psi = qiskit.quantum_info.Statevector.from_instruction(qc)
        rho_psi = qiskit.quantum_info.DensityMatrix(psi)
        # Get |psi~> = U_target|000...>
        qc1 = qiskit.QuantumCircuit(num_qubits, num_qubits)
        qc1 = qtm.nqubit.create_ghz_state(qc1, theta = theta)
        psi_hat = qiskit.quantum_info.Statevector.from_instruction(qc1)
        rho_psi_hat = qiskit.quantum_info.DensityMatrix(psi_hat)
        # Calculate the metrics
        trace, fidelity = qtm.base.get_metrics(psi, psi_hat)
        traces_ghz.append(trace)
        fidelities_ghz.append(fidelity)
        # Plot loss value in 100 steps
    print('Writting ... ' + str(num_qubits))

    np.savetxt("../../experiments/alternating_layered_ansatz/" + str(num_qubits) + "/loss_values_ghz.csv", loss_values_ghz, delimiter=",")
    np.savetxt("../../experiments/alternating_layered_ansatz/" + str(num_qubits) + "/thetass_ghz.csv", thetass_ghz, delimiter=",")
    np.savetxt("../../experiments/alternating_layered_ansatz/" + str(num_qubits) + "/traces_ghz.csv", traces_ghz, delimiter=",")
    np.savetxt("../../experiments/alternating_layered_ansatz/" + str(num_qubits) + "/fidelities_ghz.csv", fidelities_ghz, delimiter=",")



if __name__ == "__main__":
    # creating thread
    num_qubits = [3, 4, 5, 6, 7, 8, 9, 10]
    num_layers = 1
   
    t_ghz = []

    for i in num_qubits:
        t_ghz.append(multiprocessing.Process(target = run_ghz, args=(num_layers, i)))

    for i in range(0, len(num_qubits)):
        t_ghz[i].start()

    for i in range(0, len(num_qubits)):
        t_ghz[i].join()

    print("Done!")